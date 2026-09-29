import { Router } from "express";
import { product, products, searchProducts } from "../controllers/product.controller";
const router = Router();
router.get("/search", searchProducts);
router.get("/", products);
router.get("/:id", product);
export default router;
