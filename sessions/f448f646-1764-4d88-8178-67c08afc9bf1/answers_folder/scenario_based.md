## Technical Scenario-Based Questions

**1. You are tasked with designing a system to track the real-time location of delivery vehicles for a logistics company. The system must display vehicle locations on a map for a central dispatcher. Describe a high-level architecture for this system, including how vehicles would send data, how the data would be processed, and how it would be delivered to the dispatcher's web interface.**
*Model Answer:* I'd design a three-tier architecture:
1.  **Data Ingestion:** Each vehicle would have a GPS device that sends its ID, latitude, and longitude every 10 seconds via an HTTP POST request or a lightweight MQTT message to an API Gateway. This gateway would forward the data to a message queue like AWS SQS or Kafka to handle high volumes and decouple the system.
2.  **Data Processing & Storage:** A serverless function (like AWS Lambda) would trigger on each new message in the queue. It would validate the data and store the latest location for each vehicle ID in a fast, key-value database like Redis or DynamoDB, overwriting the previous entry. This ensures quick lookups of current locations.
3.  **Data Delivery & Frontend:** The dispatcher's web application would use a WebSocket connection to the backend. When a vehicle's location is updated in the database, a backend service pushes the new coordinates through the WebSocket to the frontend in real-time. The frontend JavaScript would then update the vehicle's marker on a map interface like Google Maps or Mapbox.

**2. A client's e-commerce application, built with a Python backend and a SQL database, is performing slowly. The product search feature, which filters by category, price, and user ratings, is the main bottleneck. Outline your step-by-step approach to diagnose and resolve this performance issue.**
*Model Answer:* My approach would be:
1.  **Analyze the Query:** First, I'd use the database's `EXPLAIN` or `EXPLAIN ANALYZE` command on the search query to see its execution plan. This will show if it's using full table scans instead of indexes.
2.  **Check for Missing Indexes:** The most likely culprit is missing indexes. I would ensure there are composite indexes on the columns used in the `WHERE` clause, such as `(category, price)` and `(category, user_rating)`.
3.  **Profile the Application Code:** I'd use a Python profiler to see if the bottleneck is in the application logic itself, such as inefficient data processing after the query returns.
4.  **Implement Caching:** If the same search queries are frequent, I would implement a caching layer using Redis. We could cache the results of common searches for a few minutes to reduce database load.
5.  **Database Optimization:** As a final step, I'd check for general database health, like bloated tables that might need vacuuming, or consider if the query itself can be rewritten to be more efficient.

**3. You need to build a feature that allows users to upload an image and have the system automatically tag it with relevant keywords (e.g., "sunset," "beach," "dog"). You can use pre-trained models. Describe the components you would need, the API endpoints you might design, and how you would handle the image data from request to response.**
*Model Answer:*
*   **Components:**
    1.  A frontend interface with an image upload form.
    2.  A backend service (e.g., using Flask in Python).
    3.  A pre-trained image classification/tagging model like ResNet50 or an API service like Google Vision AI.
    4.  A task queue (like Celery with Redis) to process images asynchronously, preventing the API from timing out.
*   **API Endpoint:** I'd design a single endpoint: `POST /api/v1/images/tags`.
*   **Process Flow:**
    1.  The user uploads an image via a multipart/form-data POST request to the endpoint.
    2.  The Flask backend receives the image, saves it temporarily, and places a job in the Celery task queue with the image path. It immediately returns a `202 Accepted` response with a job ID.
    3.  A Celery worker picks up the job, loads the image, and feeds it to the pre-trained model to get the tags.
    4.  The worker saves the resulting tags to a database, associated with the job ID.
    5.  The frontend can then poll a separate endpoint, like `GET /api/v1/jobs/{job_id}/status`, to check for completion and retrieve the tags.

**4. You have just completed a Figma prototype for a new user registration flow that includes social media sign-in options. The development team is about to begin implementation. What specific assets, documentation, and specifications would you provide to ensure they can build the feature exactly as designed, including handling different states like loading, error, and success?**
*Model Answer:* I would provide the following in a comprehensive handoff package:
1.  **Figma Link with Inspector Access:** The primary source, allowing developers to inspect spacing, colors, fonts, and export assets directly.
2.  **Component States:** Within Figma, I would create variants for all interactive components (buttons, input fields) showing their different states: default, hover, focused, disabled, and validation error.
3.  **User Flow Diagram:** A clear diagram illustrating the complete registration flow, including branches for social sign-in, email sign-up, error paths (e.g., "email already exists"), and success states.
4.  **Asset Exports:** I'd pre-export all necessary icons and images in SVG format to ensure they are scalable and high-quality.
5.  **A Brief Annotation Document:** A short document or comments directly in Figma explaining any complex animations or non-obvious interactions, and specifying the exact error messages to be displayed for different failure scenarios.

**5. You are building a data processing pipeline that ingests daily log files from a web server, extracts user activity metrics, and stores aggregated results in a Tableau-ready format. The log files are large and the processing is time-consuming. How would you design this pipeline to be automated, resilient to failures, and scalable as web traffic grows?**
*Model Answer:* I'd design an event-driven, serverless pipeline:
*   **Automation:** I'd use a cloud storage service like AWS S3. The pipeline would be triggered automatically whenever a new log file is uploaded to a specific S3 bucket. This can be scheduled using a cron job that moves logs daily.
*   **Resilience:**
    1.  **Decoupling:** The S3 upload event would trigger a Lambda function. If processing fails, the message can be sent to a Dead Letter Queue (DLQ) for manual inspection, so no data is lost and the pipeline isn't blocked.
    2.  **Error Handling:** The processing script (in Python using Pandas) would be wrapped in a try-except block to gracefully handle malformed log lines without crashing the entire job.
*   **Scalability:**
    1.  **Processing:** Using serverless functions like AWS Lambda allows the system to automatically scale based on the number of files. For very large files, I'd use a more robust service like AWS Glue or a containerized job on AWS Fargate, which can be configured with more memory and CPU.
    2.  **Output:** The script would process the logs, aggregate the metrics (e.g., daily active users, page views), and save the results as a Parquet or CSV file in a separate "processed" S3 bucket, which Tableau can connect to directly. This architecture is cost-effective, scalable, and robust.