#include <iostream>
#include <cstdlib>   // For system()
#include <thread>    // For sleep function
#include <chrono>    // For time handling

int main() {
    std::string ticker = "SPY";  // Define the ticker as a string

    std::cout << "Starting stock data scraper for " << ticker << " every 60 seconds...\n";

    while (true) {
        std::cout << "Running Python scraper for " << ticker << "...\n";

        // Run scraper.py and check for errors
        if (system(("python scraper.py " + ticker).c_str()) == 0) {
            std::cout << "Stock data scraped successfully.\n";
        }
        else {
            std::cerr << "Failed to run the Python script.\n";
        }


        std::cout << "Waiting 15 seconds...\n";
        std::this_thread::sleep_for(std::chrono::seconds(15));  // Wait for 15 seconds before next scrape
    }

    return 0;
}
