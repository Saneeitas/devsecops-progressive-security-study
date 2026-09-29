import { Router } from "express";
import { create, order, orders } from "../controllers/order.controller";
import { authenticate } from "../middleware/auth";
const router = Router();
router.use(authenticate);
router.post("/", create);
router.get("/", orders);
router.get("/:id", order);
export default router;
