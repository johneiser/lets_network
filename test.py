"""
Test the entire set of modules.

Usage: python3 test.py
"""
import os, unittest, lets


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()

    # Walk through module directories
    base = os.path.abspath(lets.__name__)
    for root, dirs, files in os.walk(base):
        for name in files:
            path = os.path.join(root, name)

            # Find relative path
            if path != __file__:
                [_,_,rpath] = path.partition(base + os.path.sep)
                [fpath,_,ext] = rpath.rpartition(os.path.extsep)

                # Identify modules
                if ext == "py":
                    module = os.path.extsep.join([lets.__name__, 
                        fpath.replace(os.path.sep, os.path.extsep)])

                    # Extract tests
                    tests = loader.loadTestsFromName(module)
                    suite.addTests(tests)

    return suite

if __name__ == "__main__":
    unittest.main()
