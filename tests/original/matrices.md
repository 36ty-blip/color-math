# Matrix and Tensor Original Equations

## 1. Matrix-vector multiplication

$$
\mathbf{y}=\mathbf{A}\mathbf{x}
$$

---

## 2. Matrix multiplication

$$
\mathbf{C}=\mathbf{A}\mathbf{B}
$$

---

## 3. Matrix transpose product

$$
\mathbf{G}=\mathbf{X}^{T}\mathbf{X}
$$

---

## 4. Linear system

$$
\mathbf{A}\mathbf{x}=\mathbf{b}
$$

---

## 5. Matrix inverse solution

$$
\mathbf{x}=\mathbf{A}^{-1}\mathbf{b}
$$

---

## 6. Determinant of a product

$$
\det(\mathbf{A}\mathbf{B})=\det(\mathbf{A})\det(\mathbf{B})
$$

---

## 7. Trace cyclic property

$$
\operatorname{tr}(\mathbf{A}\mathbf{B}\mathbf{C})
=
\operatorname{tr}(\mathbf{B}\mathbf{C}\mathbf{A})
$$

---

## 8. Frobenius norm

$$
\|\mathbf{A}\|_{F}
=
\sqrt{\sum_{i=1}^{m}\sum_{j=1}^{n}a_{ij}^{2}}
$$

---

## 9. Matrix derivative of quadratic form

$$
\frac{\partial}{\partial \mathbf{x}}
\left(\mathbf{x}^{T}\mathbf{A}\mathbf{x}\right)
=
(\mathbf{A}+\mathbf{A}^{T})\mathbf{x}
$$

---

## 10. Gradient of least squares

$$
\nabla_{\mathbf{x}}
\|\mathbf{A}\mathbf{x}-\mathbf{b}\|_{2}^{2}
=
2\mathbf{A}^{T}(\mathbf{A}\mathbf{x}-\mathbf{b})
$$

---

## 11. Tensor element indexing

$$
\mathcal{Y}_{ijk}
=
\sum_{p=1}^{P}\sum_{q=1}^{Q}\sum_{r=1}^{R}
\mathcal{A}_{pqr}
\mathbf{U}_{ip}
\mathbf{V}_{jq}
\mathbf{W}_{kr}
$$

---

## 12. Tensor contraction

$$
\mathbf{C}_{ij}
=
\sum_{k=1}^{n}
\mathcal{T}_{ijk}\mathbf{x}_{k}
$$

---

## 13. Einstein summation

$$
y_i=A_{ij}x_j
$$

---

## 14. Rank-one tensor outer product

$$
\mathcal{T}
=
\mathbf{a}\otimes\mathbf{b}\otimes\mathbf{c}
$$

---

## 15. Tensor mode-1 unfolding

$$
\mathbf{Y}_{(1)}
=
\mathbf{U}\mathbf{X}_{(1)}
(\mathbf{W}\otimes\mathbf{V})^{T}
$$
