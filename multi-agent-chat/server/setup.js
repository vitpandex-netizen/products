import 'dotenv/config';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { createUser, getDb } from './db.js';
import { hashPassword } from './auth.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

async function main() {
  await getDb();
  console.log('✅ Database initialized');

  const users = [
    { username: 'admin', displayName: 'Admin', password: 'admin123', role: 'admin' },
    { username: 'tester', displayName: 'Tester', password: 'tester123', role: 'user' },
  ];

  for (const u of users) {
    try {
      createUser({
        username: u.username,
        displayName: u.displayName,
        passwordHash: hashPassword(u.password),
        role: u.role,
      });
      console.log('✅ User created:', u.username);
    } catch (e) {
      if (e.message?.includes('UNIQUE')) {
        console.log('⏩ User exists:', u.username);
      } else {
        console.error('❌ Error creating', u.username, ':', e.message);
      }
    }
  }

  console.log('🎉 Setup complete!');
}

main().catch(err => { console.error(err); process.exit(1); });
