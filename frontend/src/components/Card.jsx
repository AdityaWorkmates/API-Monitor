import React from 'react';
import clsx from 'clsx';

export function Card({ className, children }) {
  return (
    <div className={clsx("rounded-xl border bg-card text-card-foreground shadow", className)}>
      {children}
    </div>
  );
}

export function CardHeader({ className, children }) {
  return <div className={clsx("flex flex-col space-y-1.5 p-6", className)}>{children}</div>;
}

export function CardTitle({ className, children }) {
  return <h3 className={clsx("font-semibold leading-none tracking-tight", className)}>{children}</h3>;
}

export function CardContent({ className, children }) {
  return <div className={clsx("p-6 pt-0", className)}>{children}</div>;
}
