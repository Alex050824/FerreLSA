import { existsSync } from 'node:fs';
import { spawn, spawnSync } from 'node:child_process';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const windows = process.platform === 'win32';
const python = join(root, 'Chatbot', '.venv', windows ? 'Scripts' : 'bin', windows ? 'python.exe' : 'python');
const vite = join(root, 'Frontend', 'node_modules', 'vite', 'bin', 'vite.js');

if (!existsSync(python)) {
  console.error('No se encontró el entorno virtual de Python en Chatbot/.venv.');
  console.error('Crealo e instalá las dependencias del backend según Frontend/README.md.');
  process.exit(1);
}
if (!existsSync(vite)) {
  console.error('No se encontraron las dependencias del frontend. Ejecutá: npm --prefix Frontend ci');
  process.exit(1);
}

const children = [];
let stopping = false;

function stop(code) {
  if (stopping) return;
  stopping = true;
  for (const child of children) {
    if (!child.pid || child.exitCode !== null || child.signalCode !== null) continue;
    if (windows) {
      // Django y Vite crean procesos hijos; cerramos el árbol completo.
      spawnSync('taskkill', ['/pid', String(child.pid), '/T', '/F'], { stdio: 'ignore', windowsHide: true });
    } else {
      try { process.kill(-child.pid, 'SIGTERM'); } catch (error) {
        if (error.code !== 'ESRCH') console.error('No se pudo detener un servidor:', error.message);
      }
    }
  }
  process.exit(code);
}

function start(name, command, args, cwd) {
  console.log(`Iniciando ${name}...`);
  const child = spawn(command, args, { cwd, stdio: 'inherit', detached: !windows, windowsHide: true });
  children.push(child);
  child.on('error', error => {
    console.error(`No se pudo iniciar ${name}: ${error.message}`);
    stop(1);
  });
  child.on('exit', (code, signal) => {
    if (stopping) return;
    console.error(`${name} se detuvo${signal ? ` (${signal})` : ` (código ${code})`}. Cerrando los servidores.`);
    stop(code || 1);
  });
}

process.on('SIGINT', () => stop(0));
process.on('SIGTERM', () => stop(0));
start('Django', python, ['-u', join(root, 'Chatbot', 'manage.py'), 'runserver'], root);
start('Vite', process.execPath, [vite, '--host', '0.0.0.0'], join(root, 'Frontend'));
