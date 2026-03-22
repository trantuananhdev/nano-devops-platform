const jwt = require("jsonwebtoken");

function signAccessToken({ tenantId, userId, role }) {
  const secret = process.env.JWT_SECRET;
  if (!secret) throw new Error("JWT_SECRET is not set");

  const payload = {
    tenant_id: tenantId,
    sub: userId,
    role,
  };

  return jwt.sign(payload, secret, { expiresIn: process.env.JWT_EXPIRES_IN || "1h" });
}

function verifyAccessToken(token) {
  const secret = process.env.JWT_SECRET;
  if (!secret) throw new Error("JWT_SECRET is not set");

  return jwt.verify(token, secret);
}

module.exports = { signAccessToken, verifyAccessToken };

