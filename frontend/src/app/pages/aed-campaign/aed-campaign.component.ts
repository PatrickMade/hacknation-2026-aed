import { DOCUMENT, isPlatformBrowser } from '@angular/common';
import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  Inject,
  OnDestroy,
  PLATFORM_ID,
  ViewChild,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { LocalizeRouterPipe } from '@gilsdav/ngx-translate-router';
import type { Map as LeafletMap } from 'leaflet';
import { EMPTY, forkJoin, Subscription } from 'rxjs';
import { switchMap, tap } from 'rxjs/operators';

import { AED_CAMPAIGN_BRAND, AED_PROVIDER_PANEL_URL } from '@app/pages/aed-campaign/aed-campaign.brand';
import { AedCampaignService, AedReportData } from '@app/pages/aed-campaign/aed-campaign.service';
import {
  AedPoint,
  computeCoverage,
  CoverageSummary,
  GminaCoverage,
  GminaFeature,
  GminaStatus,
} from '@app/pages/aed-campaign/aed-coverage';

type LoadState = 'loading' | 'ready' | 'unpublished' | 'error';

const STATUS_STYLE: Record<GminaStatus, { fillColor: string; fillOpacity: number }> = {
  // #087f45 = --mapa-serc-zielen in brand/tokens.css.
  published: { fillColor: '#087f45', fillOpacity: 0.75 },
  gap: { fillColor: '#d9480f', fillOpacity: 0.75 },
  none: { fillColor: '#ced4da', fillOpacity: 0.35 },
};

const TABLE_PREVIEW = 20;

/**
 * AED campaign page: counters and gmina coverage map from the "Raport zbiorczy AED" dataset.
 */
@Component({
  selector: 'app-aed-campaign',
  templateUrl: './aed-campaign.component.html',
  styleUrls: ['./aed-campaign.component.scss'],
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, LocalizeRouterPipe],
})
export class AedCampaignComponent implements AfterViewInit, OnDestroy {
  @ViewChild('mapRef') mapRef: ElementRef;

  readonly brand = AED_CAMPAIGN_BRAND;
  readonly providerPanelUrl = AED_PROVIDER_PANEL_URL;
  readonly statusStyle = STATUS_STYLE;
  readonly tablePreview = TABLE_PREVIEW;

  state: LoadState = 'loading';
  /** Loading of the OpenStreetMap resource, which feeds the gap map and tables. */
  osmState: 'loading' | 'ready' | 'error' = 'loading';
  osmTruncated = false;
  report: AedReportData | null = null;
  summary: CoverageSummary | null = null;
  gapGminy: GminaCoverage[] = [];
  publishedGminy: GminaCoverage[] = [];
  showAllGaps = false;
  showAllPublished = false;

  private map: LeafletMap;
  private gminy: GminaFeature[] = [];
  private subscription: Subscription;
  private destroyed = false;

  constructor(
    private aedCampaignService: AedCampaignService,
    private changeDetector: ChangeDetectorRef,
    @Inject(PLATFORM_ID) private platformId: object,
    @Inject(DOCUMENT) private document: Document,
  ) {}

  ngAfterViewInit(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }
    this.subscription = forkJoin({
      gminy: this.aedCampaignService.getGminy(),
      report: this.aedCampaignService.getReport(),
    })
      .pipe(
        // Show the counters from the small official resource first; the large OSM resource follows.
        tap(({ gminy, report }) => {
          this.gminy = gminy;
          this.report = report;
          this.updateCoverage([]);
          this.state = report ? 'ready' : 'unpublished';
          this.osmState = report?.osmResourceId ? 'loading' : 'ready';
          this.changeDetector.detectChanges();
          if (report && !report.osmResourceId) {
            this.drawMap();
          }
        }),
        switchMap(({ report }) =>
          report?.osmResourceId ? this.aedCampaignService.getOsmPoints(report.osmResourceId) : EMPTY,
        ),
      )
      .subscribe({
        next: (osmData) => {
          this.updateCoverage(osmData.points);
          this.osmTruncated = osmData.truncated;
          this.osmState = 'ready';
          this.changeDetector.detectChanges();
          this.drawMap();
        },
        error: () => {
          if (this.state === 'ready') {
            this.osmState = 'error';
          } else {
            this.state = 'error';
          }
          this.changeDetector.markForCheck();
        },
      });
  }

  private updateCoverage(osmPoints: AedPoint[]): void {
    this.summary = computeCoverage(this.report?.records || [], osmPoints, this.gminy);
    const all = Array.from(this.summary.gminy.values());
    this.gapGminy = all.filter((gmina) => gmina.status === 'gap').sort((a, b) => b.osmCount - a.osmCount);
    this.publishedGminy = all
      .filter((gmina) => gmina.status === 'published')
      .sort((a, b) => b.officialCount - a.officialCount);
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.subscription?.unsubscribe();
    this.map?.remove();
  }

  /**
   * In-page link: the portal sets <base href="/">, so a plain "#id" link would open the home page.
   * Scrolls to the section and moves focus to its heading, like the header skip links.
   */
  scrollToSection(event: Event, headingId: string): void {
    event.preventDefault();
    const heading = this.document.getElementById(headingId);
    if (heading) {
      heading.scrollIntoView({ block: 'start' });
      heading.focus({ preventScroll: true });
    }
  }

  fmt(value: number): string {
    return value.toLocaleString('pl-PL');
  }

  /** Number with the Polish plural of "gmina". */
  gminyLabel(count: number): string {
    const lastTwo = count % 100;
    const last = count % 10;
    const word = count === 1 ? 'gmina' : last >= 2 && last <= 4 && (lastTwo < 12 || lastTwo > 14) ? 'gminy' : 'gmin';
    return `${this.fmt(count)} ${word}`;
  }

  percent(part: number, total: number): string {
    return (total ? Math.round((part / total) * 1000) / 10 : 0).toLocaleString('pl-PL');
  }

  private async drawMap(): Promise<void> {
    if (!this.mapRef) {
      return;
    }
    const leaflet = await import('leaflet');
    if (this.destroyed) {
      return;
    }
    const L = leaflet.default ?? (leaflet as unknown as typeof leaflet.default);
    this.map = L.map(this.mapRef.nativeElement, {
      preferCanvas: true,
      center: [52.0, 19.4],
      zoom: 6,
      minZoom: 5,
      maxZoom: 12,
    });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution:
        'Podkład &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> (ODbL); granice gmin: PRG, GUGiK',
      maxZoom: 19,
    }).addTo(this.map);

    const coverage = this.summary.gminy;
    const collection = { type: 'FeatureCollection', features: this.gminy } as GeoJSON.FeatureCollection<
      GeoJSON.Geometry,
      GminaFeature['properties']
    >;
    const layer = L.geoJSON(collection, {
      style: (feature) => ({
        ...STATUS_STYLE[coverage.get(feature.properties.terc)?.status || 'none'],
        color: '#495057',
        weight: 0.4,
      }),
      onEachFeature: (feature, featureLayer) => {
        featureLayer.bindTooltip(this.tooltip(coverage.get(feature.properties.terc)), { sticky: true });
      },
    });
    layer.addTo(this.map);
    this.map.fitBounds(layer.getBounds());
  }

  private tooltip(gmina: GminaCoverage | undefined): string {
    if (!gmina) {
      return '';
    }
    const escape = (text: string) =>
      text.replace(
        /[&<>"']/g,
        (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char],
      );
    const operators = gmina.operators.length
      ? `<br>Instytucje: ${gmina.operators.slice(0, 5).map(escape).join(', ')}${gmina.operators.length > 5 ? '…' : ''}`
      : '';
    return `<strong>${escape(gmina.name)}</strong><br>AED w oficjalnych danych: ${gmina.officialCount}<br>AED w OpenStreetMap: ${gmina.osmCount}${operators}`;
  }
}
