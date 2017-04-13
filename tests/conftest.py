def pytest_configure(config):
    if config.option.usepdb:
        try:
            import IPython.core.debugger  # noqa
        except ImportError:
            return
        else:
            config.option.usepdb_cls = 'IPython.core.debugger:Pdb'
