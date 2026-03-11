## Technical Questions

**1. When would you choose to use a hash map versus a balanced binary search tree to store and retrieve data? Discuss the trade-offs in terms of time complexity for insertion, deletion, and search operations.**
*Model Answer:* I'd use a hash map for fast lookups, insertions, and deletions, where data order doesn't matter. Its average time complexity is O(1) for all three operations. I'd choose a balanced binary search tree when I need the data to be sorted, for example, to easily find the min/max elements or perform range queries. Its time complexity for insertion, deletion, and search is a guaranteed O(log n), which is slower than a hash map's average case but avoids the hash map's O(n) worst-case scenario with hash collisions.

**2. Explain the core differences between the Quicksort and Mergesort algorithms. Describe a scenario where Quicksort's average-case performance would be ideal, and another scenario where Mergesort's stable, worst-case performance would be more suitable.**
*Model Answer:* The core difference is their approach: Quicksort is an in-place, divide-and-conquer algorithm that partitions an array around a pivot. Mergesort is a stable, divide-and-conquer algorithm that requires extra space to merge sorted sub-arrays.
*   **Quicksort is ideal** for sorting large arrays in memory where average-case speed is critical and a rare worst-case O(n²) performance is an acceptable risk, like internal memory sorting of primitive types.
*   **Mergesort is more suitable** for sorting linked lists or when stability is required (maintaining the relative order of equal elements). Its guaranteed O(n log n) worst-case performance makes it perfect for external sorting of large datasets that don't fit in memory.

**3. What is a database index, and how does it improve query performance? Can you provide an example of a query that would benefit from an index and a situation where adding an index might actually degrade performance?**
*Model Answer:* A database index is a data structure, typically a B-tree, that improves the speed of data retrieval operations on a table. It works like an index in a book, allowing the database to find rows with specific column values without scanning the entire table.
*   **Beneficial Query:** `SELECT * FROM Users WHERE email = 'test@example.com';`. An index on the `email` column would allow the database to directly locate the matching row.
*   **Degraded Performance:** Adding indexes slows down write operations (INSERT, UPDATE, DELETE) because the database must update the table and also every index associated with it. On a table with very frequent writes and infrequent reads, an excessive number of indexes would degrade overall performance.

**4. Describe the key principles of a RESTful API. What are the standard HTTP methods, and how do they map to CRUD (Create, Read, Update, Delete) operations?**
*Model Answer:* The key principles of REST are client-server architecture, statelessness (each request contains all necessary info), cacheability, a uniform interface, and a layered system. The standard HTTP methods map to CRUD operations as follows:
*   **Create:** `POST` (e.g., `POST /users` to create a new user).
*   **Read:** `GET` (e.g., `GET /users/123` to retrieve a specific user).
*   **Update:** `PUT` (to replace an entire resource) or `PATCH` (to partially modify a resource).
*   **Delete:** `DELETE` (e.g., `DELETE /users/123` to remove a user).

**5. Explain the difference between `git merge` and `git rebase`. In a collaborative project with multiple developers, what are the primary arguments for enforcing a rebase-based workflow over a merge-based one?**
*Model Answer:* `git merge` combines two branches by creating a new "merge commit" that has both branches as parents, preserving the exact history. `git rebase` moves the entire feature branch to begin on the tip of the target branch (like `main`), rewriting the project history by creating new commits for each original commit. The primary argument for a rebase workflow is that it creates a cleaner, linear project history. This makes it easier to read, navigate, and understand the progression of the `main` branch, which simplifies debugging with tools like `git bisect`.