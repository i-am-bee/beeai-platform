/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { User } from 'next-auth';

interface UserAvatarProps {
  user?: User;
}

export default function UserAvatar(props: UserAvatarProps) {
  let userInitials = '?';
  if (props.user?.name) {
    const namesArray = props.user.name.split(' ');
    const lastIndex = namesArray.length - 1;
    userInitials = namesArray[0][0] + ' ' + namesArray[lastIndex][0];
  }
  return (
    <div className="user-icon overflow-user-menu">
      <svg width="40px" height="40px" viewBox="0 0 40 40" version="1.1" xmlns="http://www.w3.org/2000/svg">
        <g id="avatar-icon" stroke="none" strokeWidth="1" fill="none" fillRule="evenodd">
          <g id="Group">
            <circle id="Oval" stroke="#979797" cx="20" cy="20" r="19.5"></circle>
            <text id="TH" fontFamily="Helvetica" fontSize="12" fontWeight="bold" fill="#FFFFFF">
              <tspan x="10" y="24">
                {userInitials}
              </tspan>
            </text>
          </g>
        </g>
      </svg>
    </div>
  );
}
