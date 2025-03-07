import logging
from PyQt6 import QtWidgets, QtGui, QtCore
from utils import resource_path

logger = logging.getLogger(__name__)

class SplashManager:
    """Manages the application splash screen with minimum display time."""
    
    def __init__(self, app):
        """
        Initialize the splash manager.
        
        Args:
            app: QApplication instance
        """
        self.app = app
        self.splash = None
        self.spinner_movie = None
        self.start_time = None
        self.min_splash_time = 2000  # 2 seconds minimum display
        self.main_window = None  # Store the main window reference
        self._create_splash_screen()
    
    def _create_splash_screen(self):
        """Create the splash screen widget with logo and spinner."""
        # Create base widget
        base = QtWidgets.QWidget()
        base.setFixedSize(400, 300)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout(base)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Add logo
        logo_label = QtWidgets.QLabel()
        logo_pixmap = QtGui.QPixmap(resource_path("logos/viprestore_icon.png"))
        logo_label.setPixmap(logo_pixmap.scaled(
            150, 150,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation
        ))
        logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        
        # Add spinner GIF
        spinner_label = QtWidgets.QLabel()
        self.spinner_movie = QtGui.QMovie(resource_path("logos/spinner.gif"))
        # Add debug checks
        if not self.spinner_movie.isValid():
            logger.debug("Spinner GIF failed to load!")
        self.spinner_movie.setScaledSize(QtCore.QSize(32, 32))
        spinner_label.setMinimumSize(32, 32)
        spinner_label.setMovie(self.spinner_movie)
        self.spinner_movie.start()
        spinner_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(spinner_label)
        
        # Add loading text
        loading_label = QtWidgets.QLabel("Loading, please wait...")
        loading_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet("""
            QLabel {
                color: #404040;
                font-size: 14px;
                font-family: Arial;
                margin-top: 10px;
            }
        """)
        layout.addWidget(loading_label)
        
        # Set background and create pixmap
        base.setStyleSheet("background-color: white;")
        pixmap = base.grab()
        
        # Create splash screen
        self.splash = QtWidgets.QSplashScreen(pixmap, QtCore.Qt.WindowType.FramelessWindowHint)
    
    def show(self):
        """Show the splash screen and start the timer."""
        if self.splash:
            self.splash.show()
            self.app.processEvents()  # Force update
            self.start_time = QtCore.QDateTime.currentDateTime()
            logger.debug("Splash screen displayed")
            
            # Always set a hard timer to close after exactly min_splash_time
            QtCore.QTimer.singleShot(self.min_splash_time, self._check_and_finish)

    def _check_and_finish(self):
        """Check if main window is set and finish splash screen after minimum time."""
        if self.main_window:
            self._do_finish(self.main_window)
        else:
            logger.debug("Main window not set yet, waiting...")
            # Retry in 100ms if main window isn't set yet
            QtCore.QTimer.singleShot(100, self._check_and_finish)

    def close(self):
        """Close the splash screen immediately."""
        if self.splash and self.splash.isVisible():
            self.splash.close()
            logger.debug("Splash screen closed")

    def is_finish_scheduled(self):
        """Check if finish is already scheduled (for coordination with update checker)."""
        return hasattr(self, '_finish_scheduled') and self._finish_scheduled

    def finish(self, main_window):
        """
        Finish the splash screen, respecting minimum display time.
        
        Args:
            main_window: The main window that will be shown
        """
        if not self.splash:
            return
            
        # Mark that finish has been scheduled to avoid duplicate timers
        self._finish_scheduled = True
            
        # Check if minimum time has elapsed
        if self.start_time:
            elapsed = self.start_time.msecsTo(QtCore.QDateTime.currentDateTime())
            remaining = max(0, self.min_splash_time - elapsed)
            
            if remaining > 0:
                # Wait for the remaining time before finishing
                logger.debug(f"Waiting {remaining}ms to meet minimum splash time")
                QtCore.QTimer.singleShot(remaining, lambda: self._do_finish(main_window))
            else:
                # Minimum time already elapsed, finish immediately
                self._do_finish(main_window)
    
    def _do_finish(self, main_window):
        """Actually finish the splash screen and show the main window."""
        if self.splash and self.splash.isVisible():
            self.splash.finish(main_window)
            logger.debug("Splash screen finished, showing main window")