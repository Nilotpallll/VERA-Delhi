const fs = require('fs');
const path = require('path');

function getFiles(dir) {
  let results = [];
  if (!fs.existsSync(dir)) return results;
  const list = fs.readdirSync(dir);
  list.forEach(file => {
    file = path.join(dir, file);
    const stat = fs.statSync(file);
    if (stat && stat.isDirectory()) {
      results = results.concat(getFiles(file));
    } else if (file.endsWith('.ts') || file.endsWith('.tsx') || file.endsWith('.js') || file.endsWith('.jsx')) {
      results.push(file);
    }
  });
  return results;
}

const files = getFiles('apps/web/src').concat(getFiles('packages/contracts/src'));
const imports = new Set();
const importRegex = /(?:import\s+(?:[\w*\s{},]*\s+from\s+)?['"]([^'"]+)['"]|require\(['"]([^'"]+)['"]\))/g;

files.forEach(f => {
  const content = fs.readFileSync(f, 'utf8');
  let match;
  while ((match = importRegex.exec(content)) !== null) {
    const pkg = match[1] || match[2];
    if (!pkg.startsWith('.') && !pkg.startsWith('@/')) {
      const parts = pkg.split('/');
      const name = pkg.startsWith('@') ? parts[0] + '/' + parts[1] : parts[0];
      imports.add(name);
    }
  }
});

const declared = new Set([
  '@vera/contracts', 'clsx', 'lucide-react', 'next', 'react', 'react-dom', 'tailwind-merge',
  'autoprefixer', 'eslint', 'eslint-config-next', 'postcss', 'tailwindcss', 'typescript',
  '@types/node', '@types/react', '@types/react-dom', 'prettier'
]);

console.log('Detected web/contracts imports:');
imports.forEach(imp => {
  const isDeclared = declared.has(imp);
  console.log(`  ${imp.padEnd(30)} declared: ${isDeclared}`);
});
