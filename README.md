# Pattho - Personalized Study Planner

Pattho is a dynamic and comprehensive web application designed to help students, particularly those preparing for the Higher Secondary Certificate (HSC) exams in Bangladesh, to organize, track, and optimize their study process. It goes beyond a simple to-do list, offering a personalized study plan generator, detailed progress tracking, and motivational tools to keep users engaged.

## Distinctiveness and Complexity

This project satisfies the requirements for distinctiveness and complexity in several key ways, setting it apart from standard course projects like social networks or e-commerce sites.

**Distinctiveness:**

*   **Not a Social Network:** The core of Pattho is the user's personal journey through their academic syllabus. Interaction is primarily between the user and their study plan. While it includes a leaderboard for gamification, this is an auxiliary feature to motivate, not the central pillar of the application. There are no user profiles to browse, no friend requests, no direct messaging, and no content feed, which are the hallmarks of a social network.
*   **Not an E-commerce Site:** The application does not involve any commercial transactions. Its "products" are academic subjects and chapters, and its "service" is the generation of a personalized study schedule. The user's goal is to "complete" their syllabus, not to purchase goods.
*   **Unique Domain:** The application is built for a specific, complex domain: academic study planning. It models a syllabus, understands relationships between subjects, chapters, and topics, and uses this data to create a tailored experience.

**Complexity:**

The complexity of Pattho arises from the integration of its various systems and the sophisticated logic that powers its core features:

1.  **Weighted Study Plan Generation:** The most complex feature is the `generate_study_plan` function in the `planner` app. This algorithm doesn't just divide chapters evenly over a period. It creates a dynamic, weighted schedule based on:
    *   **User's Academic Stream:** The importance of a chapter changes depending on whether the user is in the Science, Commerce, or Arts stream.
    *   **Recommended Study Time:** Each chapter has a recommended study duration.
    *   **User's Schedule:** The user defines their daily study hours and the start/end dates for their plan.
    The algorithm calculates a "weight" for each chapter and allocates study minutes across the available days, ensuring a balanced and realistic schedule. This requires significant data modeling (using Django's `JSONField` for stream-specific importance) and algorithmic logic.

2.  **Detailed Progress Tracking:** Progress is not a simple binary (done/not done). The `UserProgress` model tracks five distinct dimensions for each chapter: reading the book, making notes, practicing MCQs, practicing CQs, and completing the theory. This granular data is then used to calculate a weighted `overall_progress` percentage for each chapter and aggregated to show subject-wise and total progress.

3.  **Data Analysis and Visualization:** The `analysis` app provides users with insightful charts and statistics derived from their progress data. It calculates and displays:
    *   Overall progress via a donut chart.
    *   A radar chart for field-wise progress (e.g., average completion of Notes vs. MCQs).
    *   Identification of the user's "Top Subject" and "Least Covered Subject".
    *   Identification of their "Strongest Study Type" and where they "Need Focus".
    This requires complex database queries using Django's ORM with aggregations (`Avg`, `Sum`, `Case`, `When`).

4.  **Integrated Application Suite:** Pattho is not a single-function app. It integrates a syllabus database, a dynamic planner, a multi-faceted progress tracker, a to-do list, a Pomodoro timer, and gamification elements into a single, cohesive user experience.

## File Structure and Purpose

The project is organized into several Django apps, each with a distinct responsibility:

*   `pattho/`: The main project directory containing `settings.py` and root `urls.py`.
*   `core/`: Handles the main user interface, including the base layout (`layout.html`), index page, login/registration, user profile management, and the profile completion flow.
*   `users/`: Manages user-specific data.
    *   `models.py`: Defines the `UserProfile` (extending Django's `AbstractUser`) and the detailed `UserProgress` models.
    *   `views.py`: Contains the logic for the main user dashboard, the analysis or the insight pages, and the API endpoints for updating progress.
    *   `templates/users/`: Contains the HTML for the dashboard, analysis pages.
*   `syllabus/`: Defines the academic content structure.
    *   `models.py`: Defines the `Subject`, `Chapter`, and `Topic` models, which form the backbone of the application's content.
    *   `management/commands/`: Includes custom management commands to load syllabus data into the database.
*   `planner/`: The core planning functionality.
    *   `models.py`: Defines the `StudyRoutine` model to store a user's plan.
    *   `views.py`: Contains the `generate_study_plan` algorithm and views for creating, updating, and deleting a study plan.
    *   `templates/planner/`: The HTML for the planner creation and viewing interface.
*   `activities/`: Provides supplementary study tools.
    *   `models.py`: Defines the `ToDoItem` model.
    *   `views.py`: Logic for the To-Do list and the Pomodoro timer.
    *   `templates/activities/`: HTML for the to-do and pomodoro pages.

## How to Run Your Application

To get Pattho running on your local machine, follow these steps:

1.  **Prerequisites:** Ensure you have Python 3.x and `pip` installed.

2.  **Navigate to the Project Directory:**
    The Django project is located in the `pattho` subdirectory.
    ```bash
    cd pattho
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Apply Database Migrations:**
    ```bash
    python manage.py migrate
    ```

5.  **Load Initial Syllabus Data:**
    The application requires initial data for subjects, chapters, and topics to be functional. A custom management command is provided for this.
    ```bash
    python manage.py loaddata data.json
    ```

6.  **Create a Superuser:**
    This allows you to access the Django admin interface.
    ```bash
    python manage.py createsuperuser
    ```
    Follow the prompts to create your admin username and password.

7.  **Run the Development Server:**
    ```bash
    python manage.py runserver
    ```

8.  **Access the Application:**
    Open your web browser and navigate to `http://127.0.0.1:8000/`. You can now register a new user or log in with the superuser account you created.

## Dependencies

This project relies on several Python packages. They are listed in a `requirements.txt` file. The key dependencies are:

*   **Django:** The core web framework.
*   **django-allauth:** For handling social authentication (e.g., Google login).
