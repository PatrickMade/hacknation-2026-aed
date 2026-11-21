"""One refresh of the AED report: sources (live, snapshot fallback) -> profile -> validation -> dedup -> portal."""
import tempfile

from mcod.aed_aggregate import aggregate, publish, sources, standard


def build(published=(), loaded=None):
    """Report and OSM files in the AED profile; raises RefreshError when validate.py rejects a file.

    published: records of profile resources already published in the portal (sources.published_records()[0]).
    loaded: sources.load_sources() result; default the committed snapshots.
    """
    official = sources.official_records(loaded)
    report, rejected = aggregate.check(aggregate.deduplicate(official + list(published)))
    osm, osm_rejected = aggregate.check(sources.osm_records())
    report_csv, _ = standard.to_csv(report)
    osm_csv, _ = standard.to_csv(osm)
    for name, content in (('raport', report_csv), ('osm', osm_csv)):
        with tempfile.NamedTemporaryFile(suffix='.csv') as handle:
            handle.write(content)
            handle.flush()
            errors = standard.file_errors(handle.name)
        if errors:
            raise publish.RefreshError('{}: plik niezgodny z aed-standard: {}'.format(name, '; '.join(errors[:5])))
    return {'report': report, 'rejected': rejected, 'osm': osm, 'osm_rejected': osm_rejected,
            'report_csv': report_csv, 'report_geojson': aggregate.to_geojson(report), 'osm_csv': osm_csv}


def refresh(process=True, use_live=True):
    loaded = sources.load_sources(use_live)
    published, skipped = sources.published_records()
    built = build(published, loaded)
    user = publish.bootstrap_user()
    publish.publish_sources(user, loaded, process=process)
    dataset, osm_dataset, resources = publish.publish_report(
        user, built['report_csv'], built['report_geojson'], built['osm_csv'], loaded, process=process)
    return {
        'dataset_id': dataset.pk,
        'osm_dataset_id': osm_dataset.pk,
        'resource_ids': [r.pk for r in resources],
        'sources': {item['source']['slug']: '{} {}'.format(item['origin'], item['retrieved_at']) for item in loaded},
        'records': len(built['report']),
        'published_records': len(published),
        'published_skipped': skipped,
        'rejected': [(r['source_records'][0]['source_record_id'], errors) for r, errors in built['rejected']],
        'osm_records': len(built['osm']),
        'osm_rejected': len(built['osm_rejected']),
        'flags': sorted({flag for r in built['report'] for flag in r['quality_flags']}),
    }
