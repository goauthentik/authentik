import execa from 'execa';
import { resolve } from 'path';

const bin = resolve(__dirname, './bin.js');

describe('my-command', () => {
  it('should display the help contents', async () => {
    const { stdout } = await execa(bin, ['--help']);

    expect(stdout).toContain('Usage: my-command [options]');
  });
});
