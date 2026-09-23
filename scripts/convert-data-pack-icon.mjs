import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
import sharp from 'sharp';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const inputPath = path.join(projectRoot, 'packaging', 'data-pack-icon.png');
const outputPath = path.join(projectRoot, 'packaging', 'data-pack-icon.ico');
const sizes = [256, 128, 64, 48, 32, 16];

async function createPng(size) {
  return sharp(inputPath)
    .resize(size, size, { fit: 'cover' })
    .ensureAlpha()
    .png()
    .toBuffer();
}

const images = await Promise.all(sizes.map(createPng));
const headerSize = 6;
const entrySize = 16;
const imageOffset = headerSize + entrySize * images.length;
const output = Buffer.alloc(imageOffset + images.reduce((total, image) => total + image.length, 0));

output.writeUInt16LE(0, 0);
output.writeUInt16LE(1, 2);
output.writeUInt16LE(images.length, 4);

let offset = imageOffset;
for (let index = 0; index < images.length; index += 1) {
  const size = sizes[index];
  const image = images[index];
  const entryOffset = headerSize + entrySize * index;
  output.writeUInt8(size === 256 ? 0 : size, entryOffset);
  output.writeUInt8(size === 256 ? 0 : size, entryOffset + 1);
  output.writeUInt8(0, entryOffset + 2);
  output.writeUInt8(0, entryOffset + 3);
  output.writeUInt16LE(1, entryOffset + 4);
  output.writeUInt16LE(32, entryOffset + 6);
  output.writeUInt32LE(image.length, entryOffset + 8);
  output.writeUInt32LE(offset, entryOffset + 12);
  image.copy(output, offset);
  offset += image.length;
}

await fs.writeFile(outputPath, output);
console.log(JSON.stringify({
  status: 'PASS',
  input: inputPath,
  output: outputPath,
  bytes: output.length,
  sizes,
}, null, 2));
