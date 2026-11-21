/**
 * Campaign brand (coordinator decision 2026-11-21): name, slogan, dysponent line and mark variant 1.
 * The mark path comes from the sketch brand-directions/mapa-serc/symbol-1.svg (branch feat/brand-directions).
 * When L3's final files land in brand/ on main, replace `mark` with the final symbol.
 */
export const AED_CAMPAIGN_BRAND = {
  name: 'Mapa Serc',
  slogan: 'Wszystkie AED pod ręką.',
  dysponentLine: 'Lista AED w szufladzie nikogo nie uratuje.',
  mark: {
    color: '#087F45',
    viewBox: '0 0 100 104',
    // Heart with the AED bolt as a map pin; the bolt is cut out with the even-odd fill rule.
    paths: [
      'M50 96C30 74 8 56 8 34C8 18 20 8 32 8C40 8 46 12 50 19C54 12 60 8 68 8C80 8 92 18 92 34C92 56 70 74 50 96ZM57 18L38 44H48.5L43.5 65L63 38H52Z',
    ],
  },
};

/** Provider panel, where an agent of a dysponent publishes AED data ("Dodaj dane AED"). */
export const AED_PROVIDER_PANEL_URL = 'https://admin.mcod.local/';

/** Title of the national dataset published by the portal operator. */
export const AED_REPORT_DATASET_TITLE = 'Raport zbiorczy AED';
