from lets.__module__ import Module, Mount, Container, TestCase
import os


class Postgres(Module):
    """
    Provide a postgres sql server.
    """
    images = [
        "postgres:latest",      # Cross-platform
        ]

    @classmethod
    def add_arguments(self, parser):
        parser.add_argument("-p", "--port", type=int, default=5432,
            help="listen on port (%(default)i)")
        parser.add_argument("--interface", type=str, default="0.0.0.0",
            help="listen on interface (%(default)s)")
        parser.add_argument("--user", type=str, default="postgres",
            help="database user")
        parser.add_argument("--password", type=str, default="postgres",
            help="database password")
        parser.add_argument("--db", type=str, default="postgres",
            help="database name")
        parser.add_argument("-d", "--directory", type=str,
            help="local directory to store data")

    def handle(self, input, port=5432, interface="0.0.0.0", user="postgres", password="postgres", db="postgres", directory=None):

        # Mount local directory
        volumes = {}
        if directory:
            volumes[os.path.abspath(directory)] = {
                "bind" : "/var/lib/postgresql/data"
                }

        # Launch postgres
        with Container.run("postgres:latest",
            ports={"5432/tcp" : (interface, port)},
            volumes=volumes,
            environment={
                "POSTGRES_USER": user,
                "POSTGRES_PASSWORD": password,
                "POSTGRES_DB": db,
                "PGDATA": "/var/lib/postgresql/data/pgdata",
            }) as container:

            # Print logs if requested
            for log in container.logs(stream=True, follow=True):
                self.log.logger.debug(log.strip().decode())


class PostgresTestCase(TestCase):
    images = ["postgres:latest"]

    def test_images(self):
        """
        Test that required images work on the given architecture.
        """
        import platform
        output = b""
        image = "postgres:latest"
        with Container.run(image, command="postgres --help") as container:
            output = container.output()

        self.assertRegex(output, b"Usage:",
            "Image (%s) failed for architecture: %s" % (image, platform.machine()))
