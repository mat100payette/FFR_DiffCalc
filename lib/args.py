from tap import Tap

class Arguments(Tap):
    download_charts: bool = False # If True, download charts from FFR.
    save_charts: bool = False # If True, save downloaded charts to disk.

    def process_args(self):
        # Validate arguments
        if not self.download_charts and self.save_charts:
            raise ValueError('`save_charts` can be only be true if `download_charts` is true.')