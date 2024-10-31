import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import other modules and start your application
from ui.main_window import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
