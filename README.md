# BookLover - Modern Book Review & Discovery Platform

A Goodreads-inspired web application built with **Python** and **Streamlit**. Designed around the modern layout of the [*Never Never* Goodreads book details page](https://www.goodreads.com/book/show/63120226-never-never), featuring rich community reviews, dynamic rating histograms, shelf management, and Open Library integration.

---

## 🌟 Key Features

1. **Authentic Goodreads-Style Book Details Page (`pages/1_📖_Book_Details.py`)**:
   - **Cover Hero & Actions**: Dropdown to shelf as *Want to Read*, *Currently Reading*, *Read*, or *Favorites*.
   - **Interactive Rating & Reviews**: Rate from 1 to 5 stars, write reviews with optional half-star increments (1.0 to 5.0).
   - **Spoiler Protection**: Reviews with spoilers are shielded behind a click-to-reveal expander.
   - **Rating Distribution Histogram**: Visual 5-star to 1-star bar chart displaying real percentages and vote counts.
   - **Author Spotlight & Genres**: Metadata pills, page counts, publisher, ISBN, and author information.
   - **Readers Also Enjoyed**: Recommendation carousel featuring companion books like *Verity*, *It Ends with Us*, and *The Seven Husbands of Evelyn Hugo*.

2. **Global & Local Search (`pages/2_🔍_Search_Discover.py`)**:
   - Search the local catalog or query millions of books worldwide via the **Open Library API**.
   - 1-click import: Instantly pull any book into your database and open its details page.

3. **My Bookshelf (`pages/3_📚_My_Books.py`)**:
   - Personal library dashboard with filter tabs (*Want to Read*, *Currently Reading*, *Read*, *Favorites*).
   - Track reading dates, community ratings, and move or remove books.

4. **Reader Profile & Goodreads CSV Importer (`pages/4_👤_Profile.py`)**:
   - Annual **Reading Challenge** tracker (e.g., 2026 Goal: 30 books) with interactive progress bar.
   - **Goodreads Export Importer**: Upload `goodreads_library_export.csv` to instantly populate your bookshelf with your past reading history!

---

## 🚀 How to Run

1. **Activate your environment** and navigate to this directory:
   ```bash
   cd "book review"
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Streamlit**:
   ```bash
   streamlit run app.py
   ```

4. Open your browser at **http://localhost:8501**.
