import common_site_config from '../../../sites/common_site_config.json';

const { webserver_port } = common_site_config as { webserver_port: number };

export default {
	'^/(app|api|assets|files|private)': {
		target: `http://127.0.0.1:${webserver_port}`,
		changeOrigin: true,
		ws: true,
		router(req: { headers: { host?: string } }) {
			const site_name = req.headers.host?.split(':')[0] || 'localhost';
			return `http://${site_name}:${webserver_port}`;
		},
	},
};
