# BeeAI UI

## Custom navigation

By default, the header displays the agent's name and a detail button.

You can override this with a custom navigation.
To do so, add a `nav.json` file to the root of the project.
Example:

```json
[
  {
    "label": "Playground",
    "url": "/",
    "isActive": true
  },
  {
    "label": "Cookbooks",
    "url": "https://example.com/cookbooks",
    "isExternal": true
  },
  {
    "label": "Docs",
    "url": "https://example.com/docs",
    "isExternal": true
  },
  {
    "label": "Download Granite",
    "url": "https://example.com/download-granite",
    "isExternal": true,
    "position": "end"
  }
]
```

For more details, see the [schema](./src/modules/nav/schema.ts).


## ENV

See [`.env.example`](./.env.example).


## Sidebar toggle position

By default, the hamburger menu used to toggle the sidebar is located in the header.
Its position can be configured using `VITE_APP_SIDEBAR_VARIANT` variable in `.env` file.

Two options are currently supported.
- `toggle-in-header` (default): Displays the hamburger menu inside the header, next to the app name.
- `toggle-below-header`: Displays the hamburger menu below the header with the agent name. The new session button appears next to the menu.