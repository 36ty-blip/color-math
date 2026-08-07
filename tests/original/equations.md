# Very Hard Original Equations

## 1. Triple nested power + trigonometric chain rule

$$
\frac{d}{dx}\left[\sin\left(f(g(y))^n\right)\right]^m
=
m\left[\sin\left(f(g(y))^n\right)\right]^{m-1}
\cdot
\cos\left(f(g(y))^n\right)
\cdot
n f(g(y))^{n-1}
\cdot
f'(g(y))g'(y)y'
$$

---

## 2. Logarithm of quotient with nested powers

$$
\frac{d}{dx}
\ln\left(\frac{f(y)^n}{g(y)^m}\right)
=
\frac{
n f(y)^{n-1}f'(y)y'g(y)^m
-
f(y)^n m g(y)^{m-1}g'(y)y'
}{
f(y)^n g(y)^m
}
$$

---

## 3. Exponential of square root of trigonometric composition

$$
\frac{d}{dx}
e^{\sqrt{\sin(f(y)^n)}}
=
e^{\sqrt{\sin(f(y)^n)}}
\cdot
\frac{1}{2\sqrt{\sin(f(y)^n)}}
\cdot
\cos(f(y)^n)
\cdot
n f(y)^{n-1}
\cdot
f'(y)y'
$$
