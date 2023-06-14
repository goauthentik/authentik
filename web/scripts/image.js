/* eslint-disable */
const sharp = require("sharp");
/* eslint-disable */
const fs = require("fs");

const flowBackground = `${__dirname}/src/assets/images/flow_background.jpg`;

const main = async () => {
    const tmpPath = flowBackground + ".tmp";
    await sharp(flowBackground)
        .resize(2560)
        .jpeg({
            mozjpeg: true,
        })
        .toFile(tmpPath);
    fs.promises.rename(tmpPath, flowBackground);
};

main();
