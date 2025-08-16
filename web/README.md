# MCP Server Web Application

A modular web application for the MCP Server, featuring an integrated API tester and email viewer with extensible module architecture.

## Features

- 🎯 **Modular Architecture** - Easily switch between different application modules
- 🚀 **API Testing Module** - Test all endpoints with dynamic form generation
- 📧 **Email Viewer Module** - Browse and manage emails with threading support
- 🔐 **Unified Authentication** - Single sign-on across all modules
- 🎨 **Dark/Light Theme** - Consistent theming across the application
- 📊 **Shared Services** - Common API client and configuration
- 💾 **Persistent Settings** - Saves preferences and authentication state
- 🔌 **Extensible** - Easy to add new modules using the provided template

## Usage

### Quick Start
```bash
# From the project root
python web/serve.py
# The app will open automatically in your browser
```

### Alternative Methods

#### Serve with Python
```bash
# From the web directory
cd web
python -m http.server 8090
# Then open http://localhost:8090
```

#### Serve with Node.js
```bash
# Install http-server globally if not already installed
npm install -g http-server

# From the web directory
cd web
http-server -p 8090
# Then open http://localhost:8090
```

## Getting Started

1. **Start the MCP Server**
   ```bash
   uvicorn src.api.app:app --reload --port 8000
   ```

2. **Open the Testing Tool**
   Open `web/index.html` in your browser

3. **Configure Base URL**
   - Default is `http://localhost:8000`
   - Change if your server runs on a different port

4. **Authenticate (if needed)**
   - Click "Login" button
   - Enter username and password
   - Or use "Use Token" to paste a JWT token directly

5. **Select an Endpoint**
   - Browse endpoints in the sidebar
   - Click on any endpoint to select it

6. **Configure Request**
   - Fill in path parameters (e.g., {email_id})
   - Add query parameters if needed
   - Set custom headers
   - Edit request body for POST/PUT/PATCH requests

7. **Execute Request**
   - Click the green "Execute" button
   - View the response in the right panel

## Interface Overview

### Sidebar
- **Search Bar** - Filter endpoints by name or description
- **Grouped Endpoints** - Organized by API tags (Auth, Emails, Projects, etc.)
- **Method Badges** - Color-coded HTTP methods

### Main Panel
- **Endpoint Details** - Method, path, description, and operation ID
- **Request Configuration** - Path params, query params, headers, and body
- **Response Viewer** - Status code, response time, and formatted JSON response
- **Request History** - Recent API calls with status and timing

### Header Bar
- **Base URL** - Configure the API server URL
- **Auth Status** - Shows authentication state
- **Theme Toggle** - Switch between light and dark themes

## Keyboard Shortcuts

- `Ctrl/Cmd + K` - Focus endpoint search
- `Ctrl/Cmd + Enter` - Execute current request (when endpoint selected)
- `Escape` - Close modals

## Tips

1. **Testing Authenticated Endpoints**
   - Login once and the token is saved automatically
   - Token persists across browser sessions

2. **Working with Parameters**
   - Required parameters are marked with a red asterisk (*)
   - Enum parameters show a dropdown with valid options
   - Example values are shown as placeholders

3. **Request Body Templates**
   - POST/PUT/PATCH endpoints auto-generate example JSON
   - Edit the JSON directly in the textarea
   - Invalid JSON will be sent as plain text

4. **Viewing Large Responses**
   - Response viewer has syntax highlighting
   - Large responses are scrollable
   - Copy button to copy response to clipboard

## Troubleshooting

### Cannot Connect to Server
- Verify the server is running on the correct port
- Check if the base URL is correct
- Look for CORS errors in browser console

### Authentication Issues
- Token may have expired - try logging in again
- Check if the username/password are correct
- Verify the auth endpoints are working

### No Endpoints Showing
- Check if `openapi.json` is in the web directory
- Refresh the page to reload the specification
- Check browser console for errors

## Development

The tool is built with vanilla JavaScript and requires no build process:

- `index.html` - Main HTML structure
- `css/styles.css` - Custom styles
- `js/app.js` - Main application logic
- `js/api-client.js` - API request handling
- `js/ui-builder.js` - Dynamic UI generation
- `openapi.json` - OpenAPI specification (copied from docs/)

To update the OpenAPI spec:
```bash
# From project root
cp docs/openapi.json web/openapi.json
```

## Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Opera 76+

## License

Part of the MCP Server project.