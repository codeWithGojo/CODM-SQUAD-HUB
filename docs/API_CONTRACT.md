# API Contract

All API endpoints follow REST principles.

---

## Authentication

Bearer Token

Authorization: Bearer <JWT>

---

## Standard Success Response

{
  "success": true,
  "data": {}
}

---

## Standard Error Response

{
  "success": false,
  "message": "Validation failed"
}

---

## HTTP Status Codes

200 OK

201 Created

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

500 Internal Server Error

---

## Versioning

/v1

Future versions

/v2

/v3