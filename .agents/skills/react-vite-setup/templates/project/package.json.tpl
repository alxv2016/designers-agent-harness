{
  "name": "{{name}}",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "engines": {
    "node": ">={{node_major}}"
  },
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "typecheck": "tsc -b",
    "lint": "oxlint",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "test": "vitest run --project unit",
    "test:stories": "vitest run --project storybook",
    "test:e2e": "playwright test",
    "storybook": "storybook dev --port {{storybook_port}} --exact-port --no-open",
    "build-storybook": "storybook build",
    "check": "npm run typecheck && npm run lint && npm run format:check && npm test"
  },
  "dependencies": {
{{deps}}
  },
  "devDependencies": {
{{dev_deps}}
  }
}
