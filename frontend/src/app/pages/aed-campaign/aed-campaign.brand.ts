/**
 * Campaign brand (coordinator decision 2026-11-21): name, slogan and dysponent line.
 * The mark is the final symbol from brand/logo/mapa-serc-symbol-kolor.svg (L3, APP-48), copied byte for byte
 * to frontend/src/assets/aed/ because the Angular build serves only frontend/src/assets. Use the ready file;
 * the brand book forbids redrawing or recolouring the mark.
 */
export const AED_CAMPAIGN_BRAND = {
  name: 'Mapa Serc',
  slogan: 'Wszystkie AED pod ręką.',
  dysponentLine: 'Lista AED w szufladzie nikogo nie uratuje.',
  markSrc: '/assets/aed/mapa-serc-symbol-kolor.svg',
};

/** Provider panel, where an agent of a dysponent publishes AED data ("Dodaj dane AED"). */
export const AED_PROVIDER_PANEL_URL = 'https://admin.mcod.local/';

/** Title of the national dataset published by the portal operator. */
export const AED_REPORT_DATASET_TITLE = 'Raport zbiorczy AED';
