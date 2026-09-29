import { Router } from "express";
import { me, updateMe } from "../controllers/user.controller";
import { authenticate } from "../middleware/auth";
const router = Router();
router.use(authenticate);
router.get("/me", me);
router.patch("/me", updateMe);
export default router;
