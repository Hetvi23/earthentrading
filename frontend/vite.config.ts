import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import proxyOptions from './proxyOptions';

export default defineConfig(({ command }) => {
	const isDev = command === 'serve';
	return {
		plugins: [react(), tailwindcss()],
		base: isDev ? '/earthentrading/' : '/assets/earthentrading/earthentrading/',
		server: {
			port: 8093,
			host: '0.0.0.0',
			proxy: proxyOptions,
			hmr: { port: 8093 },
			fs: {
				allow: [path.resolve(__dirname, '..'), path.resolve(__dirname, '../../..')],
			},
		},
		resolve: {
			alias: { '@': path.resolve(__dirname, './src') },
		},
		build: {
			outDir: '../earthentrading/public/earthentrading',
			emptyOutDir: true,
			target: 'esnext',
		},
	};
});
