"""Run the harness's Python tests installed in a project.

    python3 -B .ai/scripts/run_harness_tests.py [--project <root>]

The tests live in .ai/scripts/tests next to the tools they test; .ai/scripts is put on the import path. Git's
global and system configuration and any configuration passed through the environment (GIT_CONFIG_COUNT,
GIT_CONFIG_KEY_*, GIT_CONFIG_PARAMETERS) are ignored, so personal URL rewrites, signing and hooks never reach the
temporary repositories the tests create. Exit 0 when the tests pass, 1 when one fails or errors or every test is
skipped, 2 when no test is found (an empty or all-skipped run is not a pass)."""
import argparse
import json
import os
import sys
import unittest
from pathlib import Path

SCRIPTS='.ai/scripts'
TESTS=SCRIPTS+'/tests'

def run(root,stream=None):
    tests=Path(root)/TESTS
    if not tests.is_dir():return 2,{'status':'rejected','code':'harness_tests_missing:'+TESTS}
    for name in [n for n in os.environ if n in ('GIT_CONFIG_COUNT','GIT_CONFIG_PARAMETERS')
                 or n.startswith(('GIT_CONFIG_KEY_','GIT_CONFIG_VALUE_'))]:
        del os.environ[name]
    os.environ['GIT_CONFIG_GLOBAL']=os.devnull
    os.environ['GIT_CONFIG_NOSYSTEM']='1'
    sys.path.insert(0,str(Path(root)/SCRIPTS))
    suite=unittest.defaultTestLoader.discover(str(tests),top_level_dir=str(tests))
    count=suite.countTestCases()
    if not count:return 2,{'status':'rejected','code':'harness_tests_empty:'+TESTS}
    result=unittest.TextTestRunner(stream=stream or sys.stderr,verbosity=2).run(suite)
    if not result.wasSuccessful():status='failed'
    elif len(result.skipped)==count:status='all_skipped'
    else:status='passed'
    return (0 if status=='passed' else 1),{'status':status,'tests':count,'failures':len(result.failures),
                                          'errors':len(result.errors),'skipped':len(result.skipped)}

def main(argv=None):
    parser=argparse.ArgumentParser(description='Run the harness Python tests of a project (.ai/scripts/tests)')
    parser.add_argument('--project',default='.')
    args=parser.parse_args(argv)
    code,report=run(Path(args.project).resolve())
    print(json.dumps(report));return code

if __name__=='__main__':sys.exit(main())
