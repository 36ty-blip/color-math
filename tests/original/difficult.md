# Different Very Hard Original Equations

## 1. Nested logarithmic-trigonometric power chain rule

$$
\frac{d}{dx}
\left[
\ln\left(1+\cos\left(f(g(y))^p\right)\right)
\right]^q
=
q
\left[
\ln\left(1+\cos\left(f(g(y))^p\right)\right)
\right]^{q-1}
\cdot
\frac{
-\sin\left(f(g(y))^p\right)
}{
1+\cos\left(f(g(y))^p\right)
}
\cdot
p f(g(y))^{p-1}
\cdot
f'(g(y))g'(y)y'
$$

---

## 2. Exponential of rational matrix-like scalar expression

$$
\frac{d}{dx}
e^{\frac{f(y)^n}{1+g(y)^m}}
=
e^{\frac{f(y)^n}{1+g(y)^m}}
\cdot
\frac{
n f(y)^{n-1}f'(y)y'(1+g(y)^m)
-
f(y)^n m g(y)^{m-1}g'(y)y'
}{
(1+g(y)^m)^2
}
$$

---

## 3. Square root of nested tangent composition

$$
\frac{d}{dx}
\sqrt{
\tan\left(
\left[f(g(h(y)))\right]^n
\right)
}
=
\frac{1}{
2\sqrt{
\tan\left(
\left[f(g(h(y)))\right]^n
\right)
}
}
\cdot
\sec^2\left(
\left[f(g(h(y)))\right]^n
\right)
\cdot
n\left[f(g(h(y)))\right]^{n-1}
\cdot
f'(g(h(y)))g'(h(y))h'(y)y'
$$
