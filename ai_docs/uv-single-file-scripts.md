# Running TypeScript scripts with ts-node

A TypeScript script is a file intended for standalone execution, e.g., with `npx ts-node <script>.ts`. Using ts-node to execute scripts allows direct TypeScript execution without manual compilation.

## Running a script without dependencies

If your script has no dependencies, you can execute it with `npx ts-node`:

```typescript
// example.ts
console.log("Hello world");
```

```bash
$ npx ts-node example.ts
Hello world
```

Similarly, if your script depends on a module in the standard library, there's nothing more to do.

Arguments may be provided to the script:

```typescript
// example.ts
console.log(process.argv.slice(2).join(" "));
```

```bash
$ npx ts-node example.ts test
test

$ npx ts-node example.ts hello world!
hello world!
```

Additionally, your script can be read directly from stdin.

Note that if you use `ts-node` in a project with a `tsconfig.json`, it will use the TypeScript configuration. You can also run TypeScript files directly:

```bash
$ npx ts-node example.ts
```

## Running a script with dependencies

When your script requires other packages, they must be installed in your project. Install dependencies using npm:

```bash
$ npm install @types/node axios
$ npx ts-node example.ts
```

You can also install specific versions:

```bash
$ npm install @types/node@^20.0.0 axios@^1.0.0
$ npx ts-node example.ts
```

Dependencies are managed through your `package.json` file.

## Creating a TypeScript script

TypeScript supports standard npm package management. You can initialize a new project with:

```bash
$ npm init -y
$ npm install typescript ts-node @types/node
```

## Declaring script dependencies

Dependencies for TypeScript scripts are declared in your `package.json` file. Add dependencies using npm:

```bash
$ npm install @types/node axios
```

Here's an example TypeScript script using installed dependencies:

```typescript
#!/usr/bin/env npx ts-node
import axios from 'axios';

const response = await axios.get("https://peps.python.org/api/peps.json");
const data = response.data;
const entries = Object.entries(data).slice(0, 10);
console.log(entries.map(([k, v]: [string, any]) => [k, v.title]));
```

ts-node will automatically compile and run the TypeScript code using the installed dependencies.

## Using a shebang to create an executable file

A shebang can be added to make a script executable without using `npx ts-node` explicitly:

```typescript
#!/usr/bin/env npx ts-node

console.log("Hello, world!");
```

Ensure that your script is executable, e.g., with `chmod +x greet`, then run the script.

## Using alternative package registries

If you wish to use an alternative npm registry to resolve dependencies, you can configure npm:

```bash
$ npm config set registry https://example.com/npm/
$ npm install axios @types/node
```

## Locking dependencies

npm supports locking dependencies using the `package-lock.json` file format:

```bash
$ npm install
```

Running `npm install` will create or update `package-lock.json` to lock dependency versions.

## Improving reproducibility

In addition to locking dependencies, npm supports exact version specification in `package.json`:

```json
{
  "dependencies": {
    "axios": "1.0.0",
    "@types/node": "20.0.0"
  }
}
```

## Using different Node.js versions

You can use different Node.js versions with version managers like nvm:

```bash
$ # Use a specific Node.js version
$ nvm use 18
$ npx ts-node example.ts
```

## Script Execution

TypeScript scripts are executed using ts-node which compiles and runs TypeScript code on the fly.