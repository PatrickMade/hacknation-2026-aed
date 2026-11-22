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
});
