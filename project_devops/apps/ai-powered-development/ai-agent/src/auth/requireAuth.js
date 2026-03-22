const { verifyAccessToken } = require("./jwt");

function authFromReq(req) {
  const header = req.headers["authorization"];
  if (!header) return null;
  const parts = String(header).split(" ");
  if (parts.length !== 2 || parts[0].toLowerCase() !== "bearer") return null;
  return parts[1];
}

function requireAuth({ roles } = {}) {
  return (req, res, next) => {
    try {
      const token = authFromReq(req);
      if (!token) return res.status(401).json({ error: "Missing Bearer token" });

      const decoded = verifyAccessToken(token);
      const tenantId = decoded.tenant_id;
      const role = decoded.role;

      if (roles && roles.length && !roles.includes(role)) {
        return res.status(403).json({ error: "Forbidden" });
      }

      req.auth = { tenantId, role, userId: decoded.sub };
      return next();
    } catch (_err) {
      return res.status(401).json({ error: "Invalid token" });
    }
  };
}

module.exports = { requireAuth };

