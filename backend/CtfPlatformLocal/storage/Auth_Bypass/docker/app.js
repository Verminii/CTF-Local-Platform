// Dodaj na górze po require
const express = require('express');
const crypto = require('crypto');
const path = require('path');
const ejs = require('ejs');

const app = express();
const PORT = process.env.PORT || 3000;

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// ====================== CONFIG ======================
const PEPPER = process.env.PEPPER || 'k9p2';     // 4-znakowy pepper (zmieniaj przy każdym CTF)
const FLAG   = process.env.FLAG   || 'flag{ID0R_w1th_w34k_p3pp3r_1s_t00_e4sy}';

const VALID_USERS = {
  'regularuser': 'password123'
};

const ADMIN_ACCOUNTS = ["sysadmin"]

app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));

// ====================== TOKEN HELPERS ======================

/**
 * Tworzy string w formacie $5$salt$hash (SHA-256)
 * username działa jako salt, pepper jest dodawany po nim
 */
function createHashString(username) {
  const data = username + PEPPER;                    // username (salt) + pepper
  const hashHex = crypto.createHash('sha256')
                         .update(data)
                         .digest('hex');             // 64 znaki hex
  return `$5$${username}$${hashHex}`;
}

// Generuje token dla URL: base64($5$username$sha256hex)
function generateToken(username) {
  const hashString = createHashString(username);
  return Buffer.from(hashString, 'utf8').toString('base64');
}

// Dekoduje token i zwraca username jeśli jest poprawny
function getUsernameFromToken(tokenB64) {
  if (!tokenB64) return null;

  let decoded;
  try {
    decoded = Buffer.from(tokenB64, 'base64').toString('utf8');
  } catch (e) {
    return null;
  }

  if (!decoded.startsWith('$5$')) return null;

  const parts = decoded.split('$');
  if (parts.length !== 4) return null;

  const username = parts[2];
  const providedHash = parts[3];

  if (!username || providedHash.length !== 64) return null;

  // Ponowne obliczenie
  const data = username + PEPPER;
  const realHash = crypto.createHash('sha256').update(data).digest('hex');

  return (realHash === providedHash) ? username : null;
}

// ====================== ROUTES ======================

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'views', 'login.html'));
  //res.render('login')
});

app.post('/login', (req, res) => {
  const { username, password } = req.body;

  if (VALID_USERS[username] && VALID_USERS[username] === password) {
    const token = generateToken(username);
    return res.redirect(`/profile?token=${encodeURIComponent(token)}`);
  }

  res.send(`Niepoprawne dane logowania.<br><a href="/">← Powrót do logowania</a>`);
});

app.get('/profile', (req, res) => {
  const token = req.query.token || '';

  const username = getUsernameFromToken(token);

  if (!username) {
    //return res.send('Nieprawidłowy lub uszkodzony token.');
    return res.status(401).send('Nieprawidłowy lub uszkodzony token.');
  }
  if(!ADMIN_ACCOUNTS.includes(username) && !VALID_USERS[username])
  {
    return res.status(401).send('Użytkownik nie istnieje');
  }
  const isAdmin = ADMIN_ACCOUNTS.includes(username)
  res.render('profile', { 
    username: username,
    token: token,
    isAdmin: isAdmin,
    flag: isAdmin ? FLAG : null
  });
});

app.listen(PORT, '0.0.0.0' ,() => {
  console.log(`🚀 CTF challenge działa na http://localhost:${PORT}`);
  console.log(`   Pepper: ${PEPPER}`);
  console.log(`   Przykładowy token: ${generateToken('regularuser')}`);
  console.log(`   Admin: ${generateToken('sysadmin')}`);
});