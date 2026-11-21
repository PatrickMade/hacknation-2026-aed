"""One refresh of the AED report: snapshots -> profile -> validation -> dedup -> portal resources."""
import tempfile

from mcod.aed_aggregate import aggregate, publish, sources, standard


def build(published=()):
    """Report and OSM files in the AED profile; raises RefreshError when validate.py rejects a file.

    published: records of profile resources already published in the portal (sources.published_records()).
    """
    report, rejected = aggregate.check(aggregate.deduplicate(sources.official_records() + list(published)))
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


def refresh(process=True):
    published = sources.published_records()
    built = build(published)
    user = publish.bootstrap_user()
    publish.publish_sources(user, process=process)
    dataset, resources = publish.publish_report(user, built['report_csv'], built['report_geojson'], built['osm_csv'],
                                                process=process)
    return {
        'dataset_id': dataset.pk,
        'resource_ids': [r.pk for r in resources],
        'records': len(built['report']),
        'published_records': len(published),
        'rejected': [(r['source_records'][0]['source_record_id'], errors) for r, errors in built['rejected']],
        'osm_records': len(built['osm']),
        'osm_rejected': len(built['osm_rejected']),
        'flags': sorted({flag for r in built['report'] for flag in r['quality_flags']}),
    }
