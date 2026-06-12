from scraper.src.worker import run_worker
from scraper.src.database import init_db
from scraper.src.harvester import run_harvester

def main():
    print(f"{30*'='}DATABASE CREATION BEGIN{30*'='}")
    init_db()
    print(f"{30*'='}DATABASE CREATION SUCCESSFULL{30*'='}\n")
    print(f"{30*'='}BEGIN HARVESTER...{30*'='}")
    run_harvester()
    print(f"{30*'='}HARVESTER FINISHED{30*'='}\n")
    print(f"{30*'='}BEGIN WORKER...{30*'='}")
    run_worker()
    print(f"{30*'='}WORKER FINISHED{30*'='}\n")
    return None

if __name__ == "__main__":
    main()