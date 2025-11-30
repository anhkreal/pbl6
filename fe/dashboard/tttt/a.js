const fs = require('fs');
const path = require('path');

const inputDir = './tttt';
const outputDir = './tttt/output';

if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir);

fs.readdirSync(inputDir).forEach(file => {
  if (file.endsWith('.bin')) {
    const filePath = path.join(inputDir, file);
    const buffer = fs.readFileSync(filePath);
    const outName = file.replace('.bin', '.jpg');
    fs.writeFileSync(path.join(outputDir, outName), buffer);
    console.log(`Đã chuyển ${file} -> ${outName}`);
  }
});

