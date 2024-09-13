# Real Estate Agent Tools

## Intent

This project is a web application designed to streamline the process of creating and posting real estate listings to social media platforms. It aims to help real estate agents quickly generate professional, engaging posts about properties, complete with images and relevant details, and share them across multiple social media channels with ease.

## How It Works

The application follows a step-by-step process:

1. **Agent Info**: Users input their personal and company information.
2. **Address Input**: Users enter the property address, which is geocoded and displayed on a map for verification.
3. **Document Upload**: Users can upload relevant documents (e.g., property details, floor plans) to enhance the post content.
4. **Customize Prompt**: Users can modify the default prompt template used for generating the post.
5. **Generate Post**: The application uses the provided information to generate a tailored social media post.
6. **Post to Socials**: Users select images and choose which social media platforms to post to.

The backend uses AI (OpenAI's GPT models) to generate the post content based on the provided information and documents. It also integrates with various APIs for geocoding addresses and posting to social media platforms.

### OpenAI and Milvus Integration

This application leverages the power of OpenAI's language models in combination with Milvus, a vector database, to enhance the post generation process:

1. **Document Embedding**: When documents are uploaded, they are processed and converted into vector embeddings using OpenAI's embedding models.

2. **Vector Storage**: These embeddings are stored in the Milvus vector database, allowing for efficient similarity searches.

3. **Contextual Retrieval**: During post generation, the system performs a similarity search in Milvus to find the most relevant document sections based on the property details and user input.

4. **Enhanced Post Generation**: The retrieved relevant information is then used to augment the prompt sent to OpenAI's GPT model, resulting in more accurate and property-specific post content.

The goal of this integration is to create more informative and tailored social media posts by efficiently leveraging all available property information, even from lengthy documents, without overwhelming the AI model with irrelevant data.

## How to Run Locally

[... rest of the setup instructions remain the same ...]

### Backend Setup

3. Create a `.env` file in the `backend_python` directory with the following content:
   ```
   OPENAI_API_KEY=your_openai_api_key
   RENTCAST_API_KEY=your_rentcast_api_key
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key
   MILVUS_URI=http://localhost:19530
   PORT=3000
   ```

4. Start the backend server:
   ```
   poetry run uvicorn backend.main:app --reload
   ```

The backend should now be running on `http://localhost:3000`.

### Third-party Services

Some third-party services are required for the application to function properly. These are managed using Docker Compose.

1. Ensure Docker and Docker Compose are installed on your system.

2. From the root directory of the project, run:
```
docker-compose up -d
```

This will start any necessary services (e.g., databases, caching systems) defined in the `docker-compose.yml` file.

## Usage

With the frontend, backend, and third-party services running, open a web browser and navigate to `http://localhost:3001`. Follow the step-by-step process in the application to generate and post your real estate listing.

## Development

- To run backend tests: `cd backend_python && poetry run pytest`
- To run frontend tests: `cd frontend && npm test`

## Note

This application requires valid API keys for OpenAI, Google Maps, and other services. Ensure you have the necessary permissions and have correctly set up these integrations before attempting to use all features of the application. Additionally, make sure the Milvus vector database is properly configured and running for optimal performance of the document processing and post generation features.
