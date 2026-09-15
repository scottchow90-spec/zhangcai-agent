import React from 'react';
import {Composition} from 'remotion';
import {StockRecap} from './video';
export const Root: React.FC = () => <Composition id="StockRecap" component={StockRecap} durationInFrames={2100} fps={30} width={1080} height={1920} />;
