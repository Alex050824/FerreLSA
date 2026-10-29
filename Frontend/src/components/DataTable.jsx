import React from 'react';
export default function DataTable({
  columns,
  data
}) {
  return <div className="table-scroll">
    <table>
      <thead>
        <tr>
          {columns.map(c => <th key={c}>
            {c}
          </th>)}
        </tr>
      </thead>
      <tbody>
        {data.map((row, i) => <tr key={i}>
          {row.map((v, j) => <td key={j}>
            {j === row.length - 1 ? <span className={`status status--${v.toLowerCase().replaceAll(' ', '-')}`}>
              {v}
            </span> : v}
          </td>)}
        </tr>)}
      </tbody>
    </table>
  </div>;
}
