from services.storage import Storage
from services.scraper import MarksScraper
from GUI.login_window import LoginWindow

def main():
    storage = Storage("services/data/database.db")
    scraper = MarksScraper()
    Log = LoginWindow(storage, scraper)
    Log.run()

if __name__ == "__main__":
    main()