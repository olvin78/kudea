from django.apps import apps
from django.test.runner import DiscoverRunner


class ProjectDiscoverRunner(DiscoverRunner):
    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        if not test_labels:
            test_labels = [
                config.name
                for config in apps.get_app_configs()
                if config.name.startswith("applications.")
            ]

        return super().build_suite(
            test_labels=test_labels,
            extra_tests=extra_tests,
            **kwargs,
        )
