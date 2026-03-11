## Technical Questions

**1. Explain the core principles of Object-Oriented Programming (OOP). How would you apply concepts like polymorphism and inheritance in a practical Java or Python application?**
*Model Answer:* The four core principles are:
1.  **Encapsulation:** Bundling data and the methods that operate on that data within a single unit, or class.
2.  **Abstraction:** Hiding complex implementation details and showing only the essential features of the object.
3.  **Inheritance:** Allowing a new class (subclass) to inherit properties and methods from an existing class (superclass).
4.  **Polymorphism:** Allowing methods to do different things based on the object it is acting upon, often through method overriding.

For example, in Python, I could have a `Vehicle` superclass with an `__init__` method and a `drive()` method. A `Car` class could **inherit** from `Vehicle`. Then, I could create a `ElectricCar` class that also inherits from `Vehicle` but overrides the `drive()` method to account for battery usage. This is **polymorphism**, as calling `.drive()` on a `Car` object and an `ElectricCar` object would trigger different behaviors.

**2. You are given two sorted arrays, A and B, of sizes m and n respectively. Describe an efficient algorithm to find the median of the two sorted arrays combined. What is the time complexity of your proposed solution?**
*Model Answer:* The most efficient approach uses a binary search. The idea is to partition both arrays into left and right halves. We want to find a partition point in array A and a corresponding one in B such that every element in the combined left half is less than or equal to every element in the combined right half. By adjusting the partition in the smaller array using binary search, we can find this correct split. Once found, the median is either the maximum of the left halves or the average of the max of the left and min of the right, depending on whether the total number of elements is odd or even. The time complexity of this solution is O(log(min(m, n))).

**3. What is the difference between an INNER JOIN, LEFT JOIN, and FULL OUTER JOIN in SQL? Provide a simple example schema (e.g., Customers and Orders tables) to illustrate the output of each.**
*Model Answer:* Let's use a `Customers` table (CustomerID, Name) and an `Orders` table (OrderID, CustomerID).
*   **INNER JOIN:** Returns only the rows where the join condition is met in both tables. For our example, it would return only customers who have placed an order.
*   **LEFT JOIN:** Returns all rows from the left table (`Customers`) and the matched rows from the right table (`Orders`). If a customer has not placed an order, their order details will be NULL.
*   **FULL OUTER JOIN:** Returns all rows when there is a match in either the left or the right table. It would show all customers and all orders. Customers without orders would have NULL for order data, and any orders with an invalid CustomerID would have NULL for customer data.

**4. Describe the key principles of RESTful APIs. What are the primary differences between the HTTP methods GET, POST, PUT, and DELETE, and when would you use each?**
*Model Answer:* Key principles of REST include a client-server architecture, statelessness (each request from a client contains all the information needed), cacheability, and a uniform interface.
The primary HTTP methods are:
*   **GET:** Used to retrieve data from a specified resource. It is safe and idempotent (making the same call multiple times produces the same result). Use it for reading data, like `/users/123`.
*   **POST:** Used to submit new data to a resource. It is not idempotent, as calling it multiple times will create multiple new resources. Use it for creating a new entity, like `/users`.
*   **PUT:** Used to update an existing resource completely. It is idempotent. If you send the same update request multiple times, the resource's state remains the same after the first call. Use it for replacing an existing entity, like `/users/123`.
*   **DELETE:** Used to remove a specified resource. It is idempotent. Use it for deleting data, like `/users/123`.

**5. How does a hash map (or dictionary in Python) work internally? Explain the concepts of hashing, buckets, and collision resolution, and discuss its average and worst-case time complexities for insertion, deletion, and retrieval operations.**
*Model Answer:* A hash map stores key-value pairs. Internally, it uses an array of "buckets." When you insert a key-value pair, the key is passed to a **hashing function**, which computes an integer index. This index determines which **bucket** the pair should be stored in.
A **collision** occurs when two different keys hash to the same index. This is resolved using methods like **chaining**, where each bucket stores a linked list of all key-value pairs that hashed to that index.
*   **Average Time Complexity:** For insertion, deletion, and retrieval, the average complexity is O(1), assuming a good hash function that distributes keys evenly.
*   **Worst-Case Time Complexity:** If many keys collide and end up in the same bucket, the complexity degrades to O(n) because we have to search through the linked list in that bucket.