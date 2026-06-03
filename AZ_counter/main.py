from services.storage import Storage
from services.scraper import MarksScraper
from GUI.app import App

def main():
    storage = Storage("services/data/database.db")
    scraper = MarksScraper()
    App(storage, scraper)

if __name__ == "__main__":
    main()