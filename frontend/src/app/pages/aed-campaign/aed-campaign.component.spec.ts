import { of } from 'rxjs';

import { AedCampaignComponent } from './aed-campaign.component';
import { AedReportData } from './aed-campaign.service';

describe('AedCampaignComponent', () => {
  it('shows the official counters and an OSM error when the OpenStreetMap lookup fails', () => {
    const report: AedReportData = {
      datasetId: '6',
      datasetSlug: 'raport-zbiorczy-aed',
      dataDate: '2026-11-22',
      truncated: false,
      records: [
        {
          terc: null,
          operatorName: 'Szpital Demonstracyjny',
          publishers: ['Szpital Demonstracyjny'],
          confirmedOperator: true,
          lat: null,
          lon: null,
        },
      ],
      osmResourceId: null,
      osmLookupFailed: true,
    };
    const service = {
      getGminy: () => of([]),
      getReport: () => of(report),
      getOsmPoints: jest.fn(),
    };
    const changeDetector = { detectChanges: jest.fn(), markForCheck: jest.fn() };
    const component = new AedCampaignComponent(service as never, changeDetector as never, 'browser' as never, document);

    component.ngAfterViewInit();

    expect(component.state).toBe('ready');
    expect(component.osmState).toBe('error');
    expect(component.summary.records).toBe(1);
    expect(component.summary.confirmedOperators).toBe(1);
    expect(service.getOsmPoints).not.toHaveBeenCalled();
    component.ngOnDestroy();
  });

  it('uses the Polish plural of "gmina" in the map legend counts', () => {
    const component = new AedCampaignComponent({} as never, {} as never, 'browser' as never, document);

    expect([1, 2, 5, 12, 22, 2120, 2122].map((count) => component.gminyLabel(count))).toEqual([
      '1 gmina',
      '2 gminy',
      '5 gmin',
      '12 gmin',
      '22 gminy',
      '2120 gmin',
      '2122 gminy',
    ]);
  });

  it('words the demo part of a counter with the Polish plural', () => {
    const component = new AedCampaignComponent({} as never, {} as never, 'browser' as never, document);

    expect(component.demoPart(0, 'person')).toBe('');
    expect(component.demoPart(1, 'person')).toBe('w tym 1 demonstracyjny');
    expect(component.demoPart(4, 'person')).toBe('w tym 4 demonstracyjnych');
    expect(component.demoPart(1, 'thing')).toBe('w tym 1 demonstracyjny');
    expect(component.demoPart(3, 'thing')).toBe('w tym 3 demonstracyjne');
    expect(component.demoPart(12, 'thing')).toBe('w tym 12 demonstracyjnych');
    expect(component.demoPart(22, 'thing')).toBe('w tym 22 demonstracyjne');
  });
});
