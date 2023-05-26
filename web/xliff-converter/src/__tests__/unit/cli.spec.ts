import { resolve } from 'path';

describe('cli', () => {
  it('should exist', () => {
    const cli = require(resolve(__dirname, '../../cli'));

    expect(cli).toBeTruthy();
  });
});
