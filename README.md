# Chatty Shoes - AI-Powered Online Shoe Shopping

Chatty Shoes is an interactive AI agent designed to revolutionize the online shoe shopping experience. With its intuitive interface and state-of-the-art backend, Chatty Shoes facilitates seamless, engaging, and personalized conversations to assist customers in their shopping journey.

## Repository Contents

- **/backend** - contains all the code and resources related to the serverless backend based on Cloud Functions.
- **/frontend** - contains all user-facing components, written in React.

## Backend

The backend of Chatty Shoes consists of three primary components: Session Creation, Message Management, and Information Retrieval.

- **Session Creation:** Initializes user sessions for conversation management. It stores all session data including the conversation history in Firestore.
- **Message Management:** Handles FAQ in the context of the conversation and manages information retrieval operations over products as required. It utilizes the GPT-3.5-turbo language model for natural language understanding and generation.
- **Information Retrieval:** Performs semantic search over Pinecone's vectorial database to retrieve relevant product data based on user inputs.

## Frontend

The frontend serves as the user interface for the AI agent. It is designed to be user-friendly, intuitive, and interactive, thus providing a smooth customer experience. It communicates with the backend to display and relay the users' requests and the AI's responses.

Contact
For any inquiries or feedback, feel free to reach out to rincon.santi@gmail.com, [Alfredo Email] or [Lizzy_Email].
